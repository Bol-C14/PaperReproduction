; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(assert
 (let ((?x31 (bvmul ((_ zero_extend 5) ((_ extract 2 0) ((_ extract 7 0) a))) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) b))))))
(let ((?x30 (bvadd ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) c))) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ?x31))))))
(let (($x18 (and (distinct (ite (bvult a (_ bv8 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x20 (ite $x18 (bvadd ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ extract 7 0) b))) ((_ extract 7 0) c)) c)))
(and (distinct ?x20 (ite $x18 ?x30 c)) true))))))
(check-sat)
