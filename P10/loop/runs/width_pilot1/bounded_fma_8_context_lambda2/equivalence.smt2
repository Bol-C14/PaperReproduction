; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let ((?x36 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) c)))))
(let ((?x42 (bvmul ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) b))))) ((_ zero_extend 5) ((_ extract 2 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) a))))))))
(let (($x16 (and (distinct (ite (bvult a (_ bv8 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x20 (ite $x16 (bvadd ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ extract 7 0) b))) ((_ extract 7 0) c)) c)))
(and (distinct ?x20 (ite $x16 (bvadd ((_ extract 7 0) ((_ extract 7 0) ?x42)) ((_ extract 7 0) ?x36)) ?x36)) true))))))
(check-sat)
