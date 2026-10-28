; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x32 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) b)))))))))
(let ((?x31 ((_ zero_extend 13) ((_ extract 2 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) a)))))))))
(let ((?x41 (bvadd ((_ extract 15 0) ((_ extract 15 0) (bvmul ?x31 ?x32))) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) c)))))))))
(let ((?x44 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ?x41)))))
(let (($x19 (and (distinct (ite (bvult a (_ bv8 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x45 (ite $x19 ?x44 c)))
(and (not (bvult a (_ bv8 16))) (and (distinct ?x45 c) true)))))))))
(check-sat)
